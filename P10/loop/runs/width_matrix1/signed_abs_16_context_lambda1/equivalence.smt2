; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x6 ((_ extract 15 0) ((_ extract 15 0) (bvadd ((_ extract 15 0) ((_ extract 15 0) a)) ((_ extract 15 0) ((_ extract 15 0) b)))))))
(let (($x17 (and (distinct (ite (bvsge a (_ bv0 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x156 (ite $x17 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x6))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x19 (ite $x17 (bvadd ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ extract 15 0) b)) c)))
(and (distinct ?x19 ?x156) true))))))
(check-sat)
