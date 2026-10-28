; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x9 ((_ extract 15 0) (bvmul ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 2 0) b))) ((_ extract 15 0) ((_ extract 15 0) a))))))
(let ((?x1471 ((_ extract 15 0) ?x9)))
(let (($x71 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x17 (ite $x71 ((_ extract 15 0) (bvadd ?x1471 ?x1471)) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c))))))
(let ((?x114 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x71 (bvadd ?x114 ?x114) c) ?x17) true)))))))
(check-sat)
