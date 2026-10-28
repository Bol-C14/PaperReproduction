; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x48 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))))))))
(let ((?x223 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (bvneg ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))))))))))
(let (($x28 (and (distinct (ite (bvsgt (_ bv0 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x19 (and (distinct (ite (= (ite (bvsgt (_ bv249 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x21 (ite (and (and (distinct (ite (bvsgt (_ bv8 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x19) (_ bv1 1) (_ bv0 1))))
(let (($x22 (and (distinct ?x21 (_ bv0 1)) true)))
(and (distinct (ite $x22 (ite $x28 (bvneg ((_ extract 7 0) a)) a) c) (ite $x22 (ite $x28 ((_ extract 7 0) ?x223) ?x48) c)) true))))))))
(check-sat)
